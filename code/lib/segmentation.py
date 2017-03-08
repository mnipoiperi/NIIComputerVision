# File created by Inoe ANDRE the 01-03-2017

# Define functions to do the segmentation in a depthmap image
import cv2
import numpy as np
from numpy import linalg as LA
import imp
import scipy as sp
import scipy.ndimage


class Segmentation(object):
    
        # Constructor
    def __init__(self, depthImage, colorname, pos2D):
        self.depthImage = depthImage
        self.colorname = colorname
        self.pos2D = pos2D
        
#==============================================================================
#     def eraseZeros(mat):
#         """This fonction erase all zeros from the array"""
#         res = np.where(mat != 0)
#         res = np.asarray(res)
#         return res
#==============================================================================


    def findSlope(self,A,B):
        '''Get the slope of a line made from two point A and B or the distance in one axes'''
        A = A.astype(np.float32)
        B = B.astype(np.float32)
        diffY = B[1]-A[1]
        diffX = A[0]-B[0]
        dist = np.sqrt(np.square(diffY) + np.square(diffX)) 
        a = diffY/dist # normalized distance
        b = diffX/dist # normalized distance
        c = -a*A[0]-b*A[1]
        return np.array([a,b,c])
    
    def inferedPoint(self,A,a,b,c,point,T=100):
        '''Find points that are the corners of the segmented part'''
        line = self.depthImage.shape[0]
        col = self.depthImage.shape[1]
        process_y = abs(a) > abs(b) 
        if process_y:
            y = int(point[1])
            while 1:
                y = y-1
                x = int(np.round(-(b*y+c)/a))
                if A[y,x]==0:
                    x_up = x
                    y_up = y
                    break
                else:
                    distCdt = LA.norm([x,y]-point)>T
                    if distCdt:#sqrt((x-point(1))^2+(y-point(2))^2)>T:
                        x_up = x
                        y_up = y
                        break
            y = int(point[1])
            while 1:
                y = y+1
                x = int(np.round(-(b*y+c)/a))
                if A[y,x]==0:
                    x_down = x
                    y_down = y
                    break
                else:
                    distCdt = LA.norm([x,y]-point)>T
                    if distCdt:#math.sqrt((x-point(1))^2+(y-point(2))^2)>T:
                        x_down = x
                        y_down = y
                        break
    
            if x_up>x_down:
                right = [x_up, y_up]
                left = [x_down, y_down]
            else:
                left = [x_up, y_up]
                right = [x_down, y_down]
        else:#process_x
            x = int(point[0])
            while 1:
                x = x-1
                y = int(np.round(-(a*x+c)/b))
                inImage = (x>0) and (x<=col) and (y>0) and (y<=line)
                if inImage:
                    if A[int(y),int(x)]==0:
                        x_left = x
                        y_left = y
                        break
                    else:
                        distCdt = LA.norm([x,y]-point)>T
                        if distCdt:#sqrt((x-point(1))^2+(y-point(2))^2)>T
                            x_left = x
                            y_left = y
                            break
                else:
                    x_left = x+1
                    y_left = np.round(-(a*x_left+c)/b)
                    break
        
            x = int(point[0])
            while 1:
                x = x+1
                y = int(np.round(-(a*x+c)/b))
                inImage = (x>0) and (x<=col) and (y>0) and (y<=line)
                if inImage:
                    if A[int(y),int(x)]==0:
                        x_right = x
                        y_right = y
                        break
                    else:
                        distCdt = LA.norm([x,y]-point)>T
                        if distCdt:#sqrt((x-point(1))^2+(y-point(2))^2)>T
                            x_right = x
                            y_right = y
                            break
                else:
                    x_right = x-1
                    y_right = int(np.round(-(a*x_right+c)/b))
                    break
            left = [x_left, y_left]
            right = [x_right, y_right]
        return [left, right]
    
    

    def polygon(self,slopes,ref,  limit  ):
       ''' This function test the sign of alpha = a[k]*j+b[k]*i+c[k])*ref[k] 
        to know whether a point is within a polygon or not'''
       line = self.depthImage.shape[0]
       col = self.depthImage.shape[1]
       res = np.zeros([line,col],np.bool)
       alpha = np.zeros([1,limit])
       for i in range(line):
           for j in range(col):
               for k in range(limit):
                   alpha[0][k] = (slopes[0][k]*i+slopes[1][k]*j+slopes[2][k])*ref[0,k]
               alpha_positif = (alpha >= 0)
               if alpha_positif.all():
                   res[i,j]=True

       return res
        
    def polygonOutline(self,points):
        '''Find a polygon on the image through the points given in points
        /arg points : array of points which are the corners of the polygon to find'''
        line = self.depthImage.shape[0]
        col = self.depthImage.shape[1]
        im_out = np.zeros([line,col],np.uint8)
        points = points.astype(np.float64)
        n = points.shape[0]
        i = 2
        d = 0
        #delete point that are NaN
#==============================================================================
#         newPts = np.zeros([points[:,:][~np.isnan(points[:,:])].shape[0]],[points[:,:][~np.isnan(points[:,:])].shape[1]])
#         while i<=n-d:
#             if points[i,:] == points[i-1,:]:
#                 newPts[i,:]=points[i,:][~np.isnan(points[i,:])]
#                 d=d+1
#             else:
#                 i = i+1
#==============================================================================
        # trace the segment        
        ptB = np.zeros(points.shape)
        ptB[-1]=points[0]
        for i in range(0,points.shape[0]-1):
            ptB[i] = points[i+1]
        M = np.zeros([line,col],np.uint8)

        for i in range(n-d):        
            A = points[i,:]
            B = ptB[i,:]
            slopes = self.findSlope(A,B)
            if np.abs(slopes[0]) > np.abs(slopes[1]):
                if A[1] > B[1]:
                    tmp = B
                    B = A 
                    A = tmp
                for y in range(int(A[1]),int(B[1])+1):
                    x = np.round(-(slopes[1]*y+slopes[2])/slopes[0])
                    M[int(y),int(x)]= 1
            else : 
                if A[0] > B[0]:
                    tmp = B
                    B = A 
                    A = tmp
                for x in range(int(A[0]),int(B[0])+1):
                    y = np.round(-(slopes[0]*x+slopes[2])/slopes[1])
                    M[int(y),int(x)]= 1  
        ## Fill the polygon
        # Copy the thresholded image.
        im_floodfill = M.copy()
        im_floodfill = im_floodfill.astype(np.uint8)
         
        # Mask used to flood filling.
        # Notice the size needs to be 2 pixels than the image.
        h, w = M.shape[:2]
        mask = np.zeros((h+2, w+2), np.uint8)
         
        # Floodfill from point (0, 0)
        cv2.floodFill(im_floodfill, mask, (260,250), 255)
         
        # Invert floodfilled image
        im_floodfill_inv = cv2.bitwise_not(im_floodfill)
         
        # Combine the two images to get the foreground.
        im_out = M | im_floodfill_inv 
        return im_out
        #return im_floodfill
    
    def forearmLeft(self,A,B):
        '''this function segment the left arm
        /arg A is the depthImag
        /arg B is the depthImg after bilateral filtering'''
        
        # pos2D[4] = Shoulder_Left
        # pos2D[5] = Elbow_Left
        # pos2D[6] = Wrist_Left
        pos2D = self.pos2D.astype(np.float64)-1
        # First let us see the down limit thanks to the elbow and the wrist (left side)
        # FindSlopes give the slope of a line made by two point
        slopes0=self.findSlope(pos2D[5],pos2D[6])
        a_pen67 = -slopes0[1]#-b67;
        b_pen67 = slopes0[0]#a67;
        
        slopes1=self.findSlope(pos2D[5],pos2D[4])#[a65,b65,~];
        
        a_pen = slopes0[0] + slopes1[0]#a67+a65;
        b_pen = slopes0[1] + slopes1[1]#b67+b65;
        if (a_pen == b_pen) and (a_pen==0):
            a_pen = slopes1[1]#b65;
            b_pen =-slopes1[0]#a65;

        c_pen = -(a_pen*pos2D[5,0]+b_pen*pos2D[5,1])
        
        
        # find 2 points elbow
        bone1 = LA.norm(pos2D[5]-pos2D[6])#sqrt( sum( (pos2D(6,:)-pos2D(7,:)).^2 ) );
        bone2 = LA.norm(pos2D[5]-pos2D[4])#sqrt( sum( (pos2D(6,:)-pos2D(5,:)).^2 ) );
        bone = max(bone1,bone2);
        p1=B[int(pos2D[5,1]),int(pos2D[5,0])]#(pos2D(6,2),pos2D(6,1));
        p2=B[int(pos2D[6,1]),int(pos2D[6,0])]#(pos2D(7,2),pos2D(7,1));
        #threshold the image to get just the interesting part of the body
        A1 = B*(B>(min(p1,p2)-50)) * (B<(max(p1,p2)+50))
        
        # compute the intersection between the slope and the extremety of the body
        intersection_elbow=self.inferedPoint(A1,a_pen,b_pen,c_pen,pos2D[5],0.5*bone)#[left,right];
        vect_elbow = intersection_elbow[0]-pos2D[5]
        
        # find 2 points wrist
        c_pen67=-(a_pen67*pos2D[6,0]+b_pen67*pos2D[6,1])
        intersection_wrist=self.inferedPoint(A1,a_pen67,b_pen67,c_pen67,pos2D[6],bone/3)
        vect_wrist = intersection_wrist[0]-pos2D[6]
        vect67 = pos2D[6]-pos2D[5]
        vect67_pen = np.array([vect67[1], -vect67[0]])
        if sum(vect67_pen*vect_elbow)*sum(vect67_pen*vect_wrist)<0:
           x = intersection_elbow[0]
           intersection_elbow[0] = intersection_elbow[1]
           intersection_elbow[1] = x

        pt4D = np.array([intersection_elbow[0],intersection_elbow[1],intersection_wrist[1],intersection_wrist[0]])
        pt4D_bis = np.array([intersection_wrist[0],intersection_elbow[0],intersection_elbow[1],intersection_wrist[1]])
        finalSlope=self.findSlope(pt4D.transpose(),pt4D_bis.transpose())
        x = np.isnan(finalSlope[0])
        #erase all NaN in the array
        polygonSlope = np.zeros([3,finalSlope[0][~np.isnan(finalSlope[0])].shape[0]])
        polygonSlope[0]=finalSlope[0][~np.isnan(finalSlope[0])]
        polygonSlope[1]=finalSlope[1][~np.isnan(finalSlope[1])]
        polygonSlope[2]=finalSlope[2][~np.isnan(finalSlope[2])]
        midpoint = [(pos2D[5,0]+pos2D[6,0])/2, (pos2D[5,1]+pos2D[6,1])/2]
        ref= np.array([polygonSlope[0]*midpoint[0] + polygonSlope[1]*midpoint[1] + polygonSlope[2]]).astype(np.float32)
        bw_up = ( self.polygon(polygonSlope,ref,x.shape[0]-sum(x)) > 0 )#A*
        
        # pos2D[2] = Shoulder_Center
        # pos2D[3] = Head
        
        #compute slopes
        slopesSH=self.findSlope(pos2D[2],pos2D[3])
        a_pen = slopesSH[1]
        b_pen = - slopesSH[0]
        c_pen = -(a_pen*pos2D[2,0]+b_pen*pos2D[2,1])
        
        # compute the intersection between the slope and the extremety of the body
        intersection_head=self.inferedPoint(A,a_pen,b_pen,c_pen,pos2D[2])
        
        slopes215=self.findSlope(pos2D[20],pos2D[4])
        
        a_pen = slopes215[0]+slopes1[0]
        b_pen = slopes215[1]+slopes1[1]
        if (a_pen == b_pen) and (a_pen==0):
            a_pen = slopes215[1]
            b_pen = -slopes215[0]

        c_pen = -(a_pen*pos2D[4,0]+b_pen*pos2D[4,1])
        
        intersection215=self.inferedPoint(A,a_pen,b_pen,c_pen,pos2D[4])
        vect65 = pos2D[4]-pos2D[5]
        
        #vect_elbow = intersection_elbow[0]-pos2D[5]
        vect_215 = intersection215[0]-pos2D[4]  
        #cross product 
        t = np.cross(np.insert(vect_elbow, vect_elbow.shape[0],0),np.insert(vect65, vect65.shape[0],0))
        t1 = np.cross(np.insert(vect_215,vect_215.shape[0],0),np.insert(-vect65,vect65.shape[0],0))
        if t1[2]>0:
            intersection215[0] = intersection215[1]

        if t[2]<0:
            finalSlope[2] = intersection_elbow[0]
            intersection_elbow[0] = intersection_elbow[1]
            intersection_elbow[1] = finalSlope[2]

        #the upper arm need a fifth point -> Let us find it by considering it as the center of the left part of the body
        B1 = np.logical_and( (A==0),self.polygonOutline(pos2D[[5, 4, 20, 0],:]))
        f = np.nonzero(B1)
        d = np.argmin(np.sum( np.square(np.array([pos2D[20,0]-f[1], pos2D[20,1]-f[0]]).transpose()),axis=1 ))
        peakArmpit = np.array([f[1][d],f[0][d]])
        # create the upperarm polygon out the five point defining it
        ptA = np.stack((intersection_elbow[0],intersection215[0],intersection_head[0],peakArmpit,intersection_elbow[1]))
        bw_upper = (A*self.polygonOutline(ptA)>0)

        return np.array([bw_up,bw_upper])
    